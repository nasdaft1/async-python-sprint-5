from fastapi import Query

username_query = Query(
    None,
    description='Imput password', min_length=1, max_length=20)

password_query = Query(
    None,
    description='Input password', min_length=5, max_length=20,
    # проверяет, содержит ли строка как минимум одну букву,
    # одну цифру и один символ, не являющийся буквой или цифрой
    regex=r".*[A-Za-z].*[0-9].*[^A-Za-z0-9].*")
