class BaseSource:
    name = "base"
    collection_name = None

    def is_available(self) -> bool:
        return True

    def fetch_documents(self):
        """Return list of {id, name, content, metadata}"""
        raise NotImplementedError
