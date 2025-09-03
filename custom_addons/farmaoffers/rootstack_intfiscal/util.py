def convert_dict_to_list_of_tuplas(_dict_value):
    return list(_dict_value.items())


def get_key_of_value(_data, _value):
    for key, value in _data.items():
        if value == _value:
            return key
    return None
