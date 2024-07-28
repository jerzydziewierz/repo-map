import os
import sys
from pathlib import Path
from collections import defaultdict, namedtuple
import warnings
import math
from importlib import resources

import networkx as nx
from diskcache import Cache
from grep_ast import TreeContext, filename_to_lang
from pygments.lexers import guess_lexer_for_filename
from pygments.token import Token
from pygments.util import ClassNotFound
from tqdm import tqdm
import tiktoken
from pathspec import PathSpec

# Suppress FutureWarning from tree_sitter
warnings.simplefilter("ignore", category=FutureWarning)
from tree_sitter_languages import get_language, get_parser

# Define Tag namedtuple globally
Tag = namedtuple("Tag", "rel_fname fname line name kind".split())

class RepoMap:
    CACHE_VERSION = 3
    TAGS_CACHE_DIR = f".aider.tags.cache.v{CACHE_VERSION}"

    def __init__(self, root=None, map_tokens=1024, verbose=False):
        self.root = root or os.getcwd()
        self.max_map_tokens = map_tokens
        self.verbose = verbose
        self.load_tags_cache()
        self.stats = {
            'file_count': 0,
            'loc_count': 0,
            'function_count': 0,
            'total_tokens': 0
        }

    def load_tags_cache(self):
        path = Path(self.root) / self.TAGS_CACHE_DIR
        self.TAGS_CACHE = Cache(path)
        
    def save_tags_cache(self):
        self.TAGS_CACHE.close()

    def get_rel_fname(self, fname):
        return os.path.relpath(fname, self.root)

    def get_mtime(self, fname):
        try:
            return os.path.getmtime(fname)
        except FileNotFoundError:
            print(f"File not found error: {fname}")

    def get_tags(self, fname, rel_fname):
        file_mtime = self.get_mtime(fname)
        if file_mtime is None:
            return []

        cache_key = fname
        if cache_key in self.TAGS_CACHE and self.TAGS_CACHE[cache_key]["mtime"] == file_mtime:
            return self.TAGS_CACHE[cache_key]["data"]

        data = list(self.get_tags_raw(fname, rel_fname))

        self.TAGS_CACHE[cache_key] = {"mtime": file_mtime, "data": data}
        return data

    def get_tags_raw(self, fname, rel_fname):
        lang = filename_to_lang(fname)
        if not lang:
            return

        language = get_language(lang)
        parser = get_parser(lang)

        query_scm = get_scm_fname(lang)
        if not query_scm.exists():
            return
        query_scm = query_scm.read_text()

        try:
            with open(fname, 'r', encoding='utf-8') as f:
                code = f.read()
        except UnicodeDecodeError:
            print(f"Warning: File '{fname}' has encoding issues. Trying to read as binary and decode.")
            try:
                with open(fname, 'rb') as f:
                    code = f.read().decode('utf-8', errors='replace')
            except Exception as e:
                print(f"Error reading file '{fname}': {str(e)}")
                return

        if not code:
            return
        tree = parser.parse(bytes(code, "utf-8"))

        query = language.query(query_scm)
        captures = query.captures(tree.root_node)

        saw = set()
        function_count = 0
        for node, tag in captures:
            if tag.startswith("name.definition."):
                kind = "def"
                if tag.startswith("name.definition.function"):
                    function_count += 1
            elif tag.startswith("name.reference."):
                kind = "ref"
            else:
                continue

            saw.add(kind)

            yield Tag(
                rel_fname=rel_fname,
                fname=fname,
                name=node.text.decode("utf-8"),
                kind=kind,
                line=node.start_point[0],
            )

        self.stats['function_count'] += function_count
        self.stats['file_count'] += 1
        self.stats['loc_count'] += len(code.splitlines())

        if "ref" in saw:
            return
        if "def" not in saw:
            return

        try:
            lexer = guess_lexer_for_filename(fname, code)
        except ClassNotFound:
            return

        tokens = list(lexer.get_tokens(code))
        tokens = [token[1] for token in tokens if token[0] in Token.Name]

        for token in tokens:
            yield Tag(
                rel_fname=rel_fname,
                fname=fname,
                name=token,
                kind="ref",
                line=-1,
            )

    def get_ranked_tags(self, fnames):
        defines = defaultdict(set)
        references = defaultdict(list)
        definitions = defaultdict(set)

        for fname in tqdm(fnames):
            if not Path(fname).is_file():
                print(f"Repo-map can't include {fname}, it is not a normal file or no longer exists")
                continue

            rel_fname = self.get_rel_fname(fname)

            tags = list(self.get_tags(fname, rel_fname))
            if tags is None:
                continue

            for tag in tags:
                if tag.kind == "def":
                    defines[tag.name].add(rel_fname)
                    key = (rel_fname, tag.name)
                    definitions[key].add(tag)

                if tag.kind == "ref":
                    references[tag.name].append(rel_fname)

        if not references:
            references = dict((k, list(v)) for k, v in defines.items())

        idents = set(defines.keys()).intersection(set(references.keys()))

        G = nx.MultiDiGraph()

        for ident in idents:
            definers = defines[ident]
            for referencer, num_refs in defaultdict(int, [(r, references[ident].count(r)) for r in references[ident]]).items():
                for definer in definers:
                    num_refs = math.sqrt(num_refs)
                    G.add_edge(referencer, definer, weight=num_refs, ident=ident)

        try:
            ranked = nx.pagerank(G, weight="weight")
        except ZeroDivisionError:
            return []

        ranked_definitions = defaultdict(float)
        for src in G.nodes:
            src_rank = ranked[src]
            total_weight = sum(data["weight"] for _src, _dst, data in G.out_edges(src, data=True))
            for _src, dst, data in G.out_edges(src, data=True):
                data["rank"] = src_rank * data["weight"] / total_weight
                ident = data["ident"]
                ranked_definitions[(dst, ident)] += data["rank"]

        ranked_tags = []
        ranked_definitions = sorted(ranked_definitions.items(), reverse=True, key=lambda x: x[1])

        for (fname, ident), rank in ranked_definitions:
            ranked_tags += list(definitions.get((fname, ident), []))

        fnames_already_included = set(rt.rel_fname for rt in ranked_tags)

        top_rank = sorted([(rank, node) for (node, rank) in ranked.items()], reverse=True)
        for rank, fname in top_rank:
            if fname not in fnames_already_included:
                ranked_tags.append(Tag(rel_fname=fname, fname='', name='', kind='', line=-1))

        return ranked_tags

    def render_tree(self, abs_fname, rel_fname, lois):
        with open(abs_fname, 'r', encoding='utf-8') as f:
            code = f.read()
        if not code.endswith("\n"):
            code += "\n"

        context = TreeContext(
            rel_fname,
            code,
            color=False,
            line_number=False,
            child_context=False,
            last_line=False,
            margin=0,
            mark_lois=False,
            loi_pad=0,
            show_top_of_file_parent_scope=False,
        )

        context.add_lines_of_interest(lois)
        context.add_context()
        return context.format()

    def to_tree(self, tags):
        if not tags:
            return ""

        tags = sorted(tags, key=lambda t: (t.rel_fname, t.line))

        cur_fname = None
        cur_abs_fname = None
        lois = None
        output = ""

        dummy_tag = Tag(rel_fname=None, fname='', name='', kind='', line=-1)
        for tag in tags + [dummy_tag]:
            this_rel_fname = tag.rel_fname

            if this_rel_fname != cur_fname:
                if lois is not None:
                    output += "\n"
                    output += cur_fname + ":\n"
                    output += self.render_tree(cur_abs_fname, cur_fname, lois)
                    lois = None
                elif cur_fname:
                    output += "\n" + cur_fname + "\n"
                if tag.line != -1:
                    lois = []
                    cur_abs_fname = tag.fname
                cur_fname = this_rel_fname

            if lois is not None:
                lois.append(tag.line)

        output = "\n".join([line[:100] for line in output.splitlines()]) + "\n"

        return output

    def get_ignore_spec(self, directory):
        ignore_patterns = []
        ignore_files = ['.gitignore', '.aiderignore']
        
        for root, _, files in os.walk(directory):
            for ignore_file in ignore_files:
                if ignore_file in files:
                    ignore_path = os.path.join(root, ignore_file)
                    with open(ignore_path, 'r') as f:
                        patterns = f.read().splitlines()
                        rel_root = os.path.relpath(root, directory)
                        if rel_root != '.':
                            patterns = [os.path.join(rel_root, p) for p in patterns]
                        ignore_patterns.extend(patterns)
        
        return PathSpec.from_lines('gitwildmatch', ignore_patterns)

    def generate_repo_map(self, directory):
        ignore_spec = self.get_ignore_spec(directory)
        fnames = []
        for root, _, files in os.walk(directory):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, directory)
                if not ignore_spec.match_file(rel_path):
                    fnames.append(full_path)

        ranked_tags = self.get_ranked_tags(fnames)
        return self.to_tree(ranked_tags)

def get_scm_fname(lang):
    try:
        return resources.files("aider").joinpath("queries", f"tree-sitter-{lang}-tags.scm")
    except KeyError:
        return Path()

def count_tokens(text):
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def main():
    if len(sys.argv) == 1:
        directory = "."
    elif len(sys.argv) == 2:
        directory = sys.argv[1]
    else:
        print("Usage: python repo_map_generator.py [directory]")
        print("If no directory is specified, the current directory will be used.")
        sys.exit(1)
    repo_map = RepoMap(root=directory)
    try:
        result = repo_map.generate_repo_map(directory)
        print(result)

        # Calculate total tokens
        repo_map.stats['total_tokens'] = count_tokens(result)

        # Print statistics
        print("\nRepository Statistics:")
        print(f"Total files: {repo_map.stats['file_count']}")
        print(f"Total lines of code: {repo_map.stats['loc_count']}")
        print(f"Total functions: {repo_map.stats['function_count']}")
        print(f"Total tokens needed to express entire repo: {repo_map.stats['total_tokens']}")
    finally:
        repo_map.save_tags_cache()

if __name__ == "__main__":
    main()
