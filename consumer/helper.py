"""Helper for few usage """


def extract_delimited_string(data, delimiter=":"):
    """    Extracts strings delimited by a specified delimiter from a given string.

    Args:
        data: The string to extract from.
        delimiter: The delimiter to split the string by (default is ":").

    Returns:
        A list of extracted strings.
    """

    if delimiter not in data:
        return [data]  # No delimiter found, return the entire string

    return data.split(delimiter)


def delivery_report(err, m):
    """Helper to get callback delivery report"""
    if err is not None:
        print(f"Message -{m}, delivery failed: {err}")
    else:
        print(f'Message delivered to { m.topic()} [partition - {m.partition()}]')


def deconstruct_payload(decoded_message):
    """One liner deconstruct message"""
    return [decoded_message[key] for key in decoded_message]


def callback_supabase(response):
    """Handle callback supabase"""
    if response.status_code == 200:
        print("Message inserted successfully!")
    else:
        error = response.error
        print(f"Error inserting message: {error['message']}")
