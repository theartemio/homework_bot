STRING = None

class StringNotFound(Exception):
    pass


try:
    STRING != None
except Exception:
    print(123)
    raise StringNotFound

print('unaccessuble part')