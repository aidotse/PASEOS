def is_notebook() -> bool:
    """This function returns "True" if the execution is performed inside a jupyter noteook. Otherwise False.

    Returns:
        bool: True if this function is executed inside a Jupyter book. Otherwise, False
    """
    try:
        shell = get_ipython().__class__.__name__  # type: ignore
        if shell == "ZMQInteractiveShell":
            return True  # Jupyter notebook or qtconsole
        elif shell == "TerminalInteractiveShell":
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False
