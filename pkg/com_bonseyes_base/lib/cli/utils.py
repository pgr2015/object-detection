
def format_table(data, header=None):

    output = ""

    if len(data) == 0:
        return output

    # this stores the width of each column
    columns = [0] * len(data[0])

    # compute size of head field
    for row in data:
        for idx, field in enumerate(row):
            columns[idx] = max(len(field), columns[idx])

    # compute size of each headers
    if header is not None:
        for idx, field in enumerate(header):
            columns[idx] = max(len(field), columns[idx])

    # add some padding between columns and compute the full width
    full_size = 0
    for idx in range(len(columns)):
        columns[idx] += 4
        full_size += columns[idx]

    # print the header
    if header is not None:
        for idx, field in enumerate(header):
            output += field + (columns[idx] - len(field)) * ' '

        output += "\n" + ("-" * full_size) + "\n"

    # print the data
    for row in data:
        for idx, field in enumerate(row):
            output += field + (columns[idx] - len(field)) * ' '
        output += "\n"

    return output
