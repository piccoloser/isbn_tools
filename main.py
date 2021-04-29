from inspect import cleandoc
import json
import math
import os
import re
import textwrap
import urllib.request

def get_int(message: str) -> int:

    # get an integer, repeat if invalid
    while True:
        response = input(message)

        if response.isdigit():
            return int(response)

def rm_dashes(isbn: str) -> str:

    # remove dashes from input
    return isbn.replace("-", "")

def check_isbn_format(isbn: str) -> str:

    # check input against valid regex pattern
    return re.match(
        "(?:\d{3})?\d{9}[\d|X]$",
        isbn,
        flags=re.I
    )

def isbn_list_from_file(path) -> list:
    output = []
    with open(path, "r") as f:
        lines = f.readlines()
        for line in lines:
            output.append(rm_dashes(line.strip()))

    return output
        

def get_isbn(message: str, length = None) -> str:

    # get a valid ISBN number, repeat if invalid
    while True:
        response = input(message)

        if os.path.isfile(response):
            return isbn_list_from_file(response)

        else:
            response = rm_dashes(response)
            
        if check_isbn_format(response):
            if (
                    len(response) == length or
                    not length and
                    len(response) in set((10, 13))
            ): return response

            else:
                if length:
                    print(
                        f"Incorrect formatting for ISBN-{length}. "
                        "Please try again.\n"
                    )
                else:
                    print("Invalid ISBN. Please try again.")

def check_isbn_10(isbn: str) -> tuple:
    char_sum = 0
    for index, c in enumerate(isbn, 1):
        if index == len(isbn): break
        char_sum += int(c)*index

    check_num = char_sum % 11

    if isbn[-1].lower() == 'x':
        return (check_num == 10, str(check_num))
    return (check_num == int(isbn[-1]), check_num)

def check_isbn_13(isbn: str) -> tuple:
    char_sum = 0
    for index, c in enumerate(isbn, 1):
        if index == len(isbn): break
        char_sum += int(c)*[3, 1][index % 2]

    check_num = 10 - char_sum % 10

    if isbn[-1] == '0':
        return (check_num == 10, check_num)
    return (check_num == int(isbn[-1]), check_num)

def convert_isbn_10(isbn: str) -> str:
    if not check_isbn_10(isbn)[0]:
        return "invalid isbn-10"
        
    new_isbn = f"978{isbn}"
    _, check_num = check_isbn_13(new_isbn)

    return new_isbn[:-1] + str(check_num)

def convert_isbn_13(isbn: str) -> str:
    if not check_isbn_13(isbn)[0]:
        return "invalid isbn-13"

    new_isbn = rm_dashes(isbn)[3:]
    _, check_num = check_isbn_10(isbn)

    if check_num == 10: check_num = 'x'
    return new_isbn[:-1] + str(check_num)


def main():
    base_api_link = "https://www.googleapis.com/books/v1/volumes?q=isbn:"
    fcn_result_message = ""
    menu_width = 39

    while True:
        message = "Enter an ISBN-$ or a file path: "
        print(cleandoc(f"""
        {'-' * menu_width}
        {'Python ISBN Conversion Menu'.center(menu_width, ' ')}

        1. Verify the check digit of an ISBN-10
        2. Verify the check digit of an ISBN-13
        3. Convert an ISBN-10 to an ISBN-13
        4. Convert an ISBN-13 to an ISBN-10
        5. Get book information from ISBN
        6. Exit
        {'-' * menu_width}
        { fcn_result_message.center(menu_width, ' ') }
        """))

        print()
        user_response = get_int("Choose an option (1-6): ")
        if user_response == 6: break

        # get book info from google api using isbn
        if user_response == 5:
            isbn = get_isbn("Enter an ISBN-10 or ISBN-13: ")

            with urllib.request.urlopen(f"{base_api_link}{isbn}") as f:
                text = f.read()

            decoded_text = text.decode("utf-8")
            obj = json.loads(decoded_text)
            volume_info = obj["items"][0]
            authors = volume_info["volumeInfo"]["authors"]

            print(cleandoc(f"""
                {'-' * menu_width}
                Title: {volume_info["volumeInfo"]["title"]}
                {'-' * menu_width}
                Summary:
                    {
                        textwrap.fill(
                            volume_info["searchInfo"]["textSnippet"],
                            width = math.floor(menu_width * 1.5),
                            subsequent_indent = ' ' * 20
                        )
                    }
                
                Author(s): {", ".join(authors)}
                Page Count: {volume_info["volumeInfo"]["pageCount"]}
                Language: {volume_info["volumeInfo"]["language"]}
                {'-' * menu_width}

            """))

        # odd menu items deal with 10 digits, even with 13
        if user_response in set(range(1, 5)):
            length = [13, 10][user_response % 2]
            message = message.replace("$", f"{length}")
            isbn = get_isbn(message, length)

            if isinstance(isbn, str):
                # run selected function (1-4)
                fcn_result = [
                    check_isbn_10,
                    check_isbn_13,
                    convert_isbn_10,
                    convert_isbn_13,
                ][user_response - 1](isbn)

            else:
                user_choice = [
                    check_isbn_10,
                    check_isbn_13,
                    convert_isbn_10,
                    convert_isbn_13,
                ][user_response - 1]

                with open("isbn_log.txt", "a") as f:
                    for line in isbn:
                        if not line.strip(): continue

                        fcn_result = user_choice(line)
                        
                        if isinstance(fcn_result[0], bool):
                            f.write(
                                f"{line}"
                                "\t\t<- "
                                f"{'VALID' if fcn_result[0] else 'INVALID'}\n"
                            )
                        else:
                            f.write(
                                f"{line}\t\t-> {fcn_result.upper()}\n"
                            )
                continue

            if isinstance(fcn_result, tuple):
                fcn_result_message = (
                    f"{'VALID' if fcn_result[0] else 'INVALID'} "
                    f"ISBN-{length}"
                )
            else:
                fcn_result_message = f"Result: {isbn} -> {fcn_result.upper()}"


        else: continue
    quit()


if __name__ == "__main__":
    main()