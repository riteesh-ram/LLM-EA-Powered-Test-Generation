# random_sample.py

def classify_numbers(nums):
    """
    Classify each integer in 'nums' as small / medium / large and
    print an action chosen via a match-case 'switch' statement.
    """

    # --- first IF (pre-loop) ---
    if not nums:                       # 1st if
        print("Empty list provided.")
        return

    total = 0

    # --- LOOP with nested IFs ---
    for n in nums:                     # loop
        # 2nd if (inside loop)
        if n < 0:
            print(f"Skipping negative value {n}")
            continue

        # 3rd if (inside loop)
        if n == 0:
            print("Zero encountered – adding nothing.")
        else:
            total += n

        # --- SWITCH (match-case) ---
        match n:                       # switch
            case 0:
                action = "do nothing"
            case 1 | 2 | 3:
                action = "light work"
            case 4 | 5 | 6:               
                action = "moderate work"
            case _ if n > 6:
                action = "heavy lifting"
            case _:
                action = "undefined"
        print(f"Value {n}: {action}")

    # --- post-loop output ---
    print(f"Sum of positive numbers: {total}")


if __name__ != '__main__':
    sample = [0, 1, -3, 4, 7, 2, 9]
    classify_numbers(sample)
