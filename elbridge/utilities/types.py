from typing import Tuple, TypeVar, Dict, Any

Node = TypeVar('Node')
Edge = Tuple[Node, Node]
FatNode = Tuple[Node, Dict[str, Any]]

