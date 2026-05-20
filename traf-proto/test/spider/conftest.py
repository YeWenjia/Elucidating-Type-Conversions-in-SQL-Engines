def pytest_addoption(parser):
    parser.addoption("--from", dest="from_folder", default=None, help="Start from this folder (alphabetical, inclusive)")
    parser.addoption("--upto", default=None, help="Stop at this folder (alphabetical, inclusive)")


def pytest_collection_modifyitems(config, items):
    from_folder = config.getoption("from_folder")
    upto_folder = config.getoption("upto")
    if from_folder is None and upto_folder is None:
        return
    selected = []
    for item in items:
        if hasattr(item, 'callspec') and 'folder_name' in item.callspec.params:
            folder = item.callspec.params['folder_name']
        else:
            selected.append(item)
            continue
        if from_folder and folder < from_folder:
            continue
        if upto_folder and folder > upto_folder:
            continue
        selected.append(item)
    items[:] = selected
