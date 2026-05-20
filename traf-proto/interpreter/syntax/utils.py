"""Utility functions for syntax processing"""


def changeb(v):
    """
    Convert a BValue to a boolean for truth testing.
    
    Args:
        v: A BValue object
        
    Returns:
        Boolean value suitable for truth testing
    """
    if v.erase() == 0:
        return False
    elif v.erase() == 1:
        return True
    elif v.erase() == None:
        return False
    else:
        return v.erase()
