from typing import Tuple, TypeVar, Dict, Any, Set

Node = TypeVar('Node')
Edge = Tuple[Node, Node]
FatNode = Tuple[Node, Dict[str, Any]]
Component = Set[Node]
