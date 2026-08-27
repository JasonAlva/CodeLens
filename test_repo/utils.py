import json


def format_user(user):
    data = {
        "name": user.name,
        "age": user.age,
    }

    return json.dumps(data)


def calculate_age_in_months(age):
    return age * 12