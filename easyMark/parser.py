__all__ = ['split_text', 'join_text_list']


def split_text(text: str) -> list:
    return text.split()

def join_text_list(text_list: list, sep: str = ' ') -> str:
    # Check types in text_list
    # if not isinstance(text_list, list):
    #     raise TypeError("text_list must be a list of str")
    # non_str = [(i, type(v).__name__) for i, v in enumerate(text_list) if not isinstance(v, str)]
    # if non_str:
    #     details = ', '.join(f"{idx}:{typ}" for idx, typ in non_str)
    #     raise TypeError(f"All items in text_list must be str; non-str items at {details}")
    return sep.join(text_list)