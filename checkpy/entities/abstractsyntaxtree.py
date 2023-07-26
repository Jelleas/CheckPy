import checkpy
import checkpy.entities.exception
import ast
from typing import Optional, List

__all__ = ["AbstractSyntaxTree"]

class AbstractSyntaxTree:
    """
    An 'in' and 'not in' comparible AbstractSyntaxTree for any ast.Node (any type of ast.AST).
    For instance:

    ```
    assert ast.For in AbstractSyntaxTree() # assert that a for-loop is present
    assert ast.Mult in AbstractSyntaxTree() # assert that multiplication is present
    ```
    """
    def __init__(self, fileName: Optional[str]=None):
        # Keep track of any nodes found from last search for a pretty assertion message 
        self.foundNodes: List[ast.AST] = []

        # Similarly hold on to the source code
        self.source: str = checkpy.static.getSource(fileName=fileName)

    def __contains__(self, item: type) -> bool:
        if item.__module__ != ast.__name__:
            raise checkpy.entities.exception.CheckpyError(
                f"{item} is not of type {ast.AST}. Can only search for {ast.AST} types in AbstractSyntaxTree."
            )
        
        self.foundNodes = checkpy.static.getAstNodes(item, source=self.source)        
        return bool(self.foundNodes)
