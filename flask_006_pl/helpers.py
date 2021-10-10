ALLOWED_EXTENSIONS = ['png']


def check_ext(filename):
    ext = filename.rsplit('.', 1)[1]
    return ext.lower() in ALLOWED_EXTENSIONS


def check_password(pas: str) -> dict:
    ascii_error = not pas.isascii()
    length_error = len(pas) < 8
    digit_error = not any(char.isdigit() for char in pas)
    lowercase_error = not any(char.islower() for char in pas)
    uppercase_error = not any(char.isupper() for char in pas)
    symbol_error = not any(char in "!#$%&\'\"()*+,-.^_`" for char in pas)
    space_error = any(char.isspace() for char in pas)
    password_ok = not (ascii_error
                       or length_error
                       or digit_error
                       or lowercase_error
                       or uppercase_error
                       or symbol_error
                       or space_error)
    return {
        'password_ok': password_ok,
        'В пароле недопустимые символы': ascii_error,
        'Слишком короткий пароль': length_error,
        'В пароле нет цифр': digit_error,
        'В пароле нет заглавных букв': uppercase_error,
        'В пароле нет маленьких букв': lowercase_error,
        'В пароле нет символов: !#$%&\'\"()*+,-.^_`': symbol_error,
        'В пароле не должно быть пробелов': space_error
    }
