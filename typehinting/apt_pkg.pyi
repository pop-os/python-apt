from typing import Any, Dict, Iterable, Iterator, List, Mapping, Tuple, Union

class CdromProgress:
    pass

class Cdrom:
    def add(self, progress: CdromProgress) -> bool: ...
    def ident(self) -> bool: ...

def gettext(msg: str) -> str: ...

class Configuration(dict):
    def find_file(self, key: str, default: str="") -> str: ...
    def find_dir(self, key: str, default: str="") -> str: ...
    def dump(self) -> str: ...
    def find(self, key: str, default: object=None) -> str: ...
    def find_b(self, key: str, default: bool=False) -> bool: ...
    def set(self, key: str, value: str) -> None: ...
    def value_list(self, key: str) -> List[str]: ...
    def clear(self, root: object=None) -> None: ...

config = Configuration()

def init() -> None: ...
def init_config() -> None: ...
def init_system() -> None: ...

# FIXME: this is really a file-like object
def md5sum(o: Any) -> str: ...

class Dependency():
    comp_type: str
    comp_type_deb: str
    target_pkg: Package
    target_ver: str
    dep_type_untranslated: str
    def all_targets(self) -> List[Version]: ...

class Package():
    name: str

class Version():
    ver_str: str
    hash: int
    file_list: List[PackageFile]
    translated_description: Description
    installed_size: int
    size: int
    arch: str
    downloadable: bool
    id: int
    section: str
    priority: int
    priority_str: str
    provides_list: List[Tuple[str,str,str]]
    def parent_pkg(self) -> Package: ...

class Description():
    file_list: List[PackageFile]

class PackageRecords():
    homepage: str
    short_desc: str
    long_desc: str
    source_pkg: str
    source_ver: str
    record: str
    filename: str
    md5_hash: str
    sha1_hash: str
    sha256_hash: str

class PackageFile(Iterable):
    architecture: str
    archive: str
    codename: str
    component: str
    filename: str
    id: int
    index_type: str
    label: str
    not_automatic: bool
    not_source: bool
    origin: str
    site: str
    size: int
    version: str

class TagFile(Iterable):
    def __init__(self, file: object, bytes: bool=False) -> None: ...
    def __iter__(self) -> Iterator[TagSection]: ...

class TagSection(Mapping):
    def __init__(self, str) -> None: ...
    def __getitem__(self, key: object) -> str: ...
    def __contains__(self, key: object) -> bool: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[str]: ...

def version_compare(a: str, b: str) -> int: ...

def get_lock(file: str, errors: bool=False) -> int: ...
def pkgsystem_lock() -> None: ...
def pkgsystem_unlock() -> None: ...
def read_config_file(configuration: Configuration, path: str) -> None: ...
def read_config_dir(configuration: Configuration, path: str) -> None: ...

SELSTATE_HOLD: int

class Acquire:
    items: List[AcquireItem]
    # FIXME: progress must be apt.progress.base
    def __init__(self, progress: object=None) -> None: ...
    def run(self) -> int: ...

class AcquireItem:
    complete: bool
    desc_uri: str
    destfile: str
    error_text: str
    filesize: int
    is_trusted: bool
    status: int
    STAT_ERROR: int
    STAT_DONE: int

class AcquireFile(AcquireItem):
    def __init__(self, owner: Acquire, uri: str, md5: str="", size: int=0, descr: str="", short_descr: str="", destdir: str="", destfile: str="") -> None: ...

class IndexFile:
    def archive_uri(self, path: str) -> str: ...
    describe: str
    exists: bool
    has_packages: bool
    is_trusted: bool
    label: str
    size: int
    
class SourceRecords:
    def lookup(self, name: str) -> bool: ...
    def restart(self) -> None: ...
    def step(self) -> bool: ...
    binaries: List[str]
    version: str
    files: List[Tuple[str, int, str, str]]
    index: IndexFile
    package: str

class ActionGroup:
    def __init__(self, depcache: DepCache) -> None: ...

class SourceList():
    def read_main_list(self) -> None: ...

class PackageManager():
    def __init__(self, depcache: DepCache) -> None: ...
    def get_archives(self, fetcher: Acquire, list: SourceList, recs: PackageRecords) -> bool: ...

class DepCache():
    pass

def upstream_version(ver: str) -> str: ...
    
