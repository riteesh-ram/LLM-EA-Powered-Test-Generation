# --- Spiral Matrix Code ---

def spirallyTraverse(mat):
    """
    Traverses a matrix in a spiral (clockwise) fashion.
    """
    if not mat or not mat[0]:
        return []
        
    m = len(mat)
    n = len(mat[0])
    res = []
    vis = [[False] * n for _ in range(m)]

    # Changes in row and column indices for each direction (Right, Down, Left, Up)
    dr = [0, 1, 0, -1]
    dc = [1, 0, -1, 0]

    r, c, idx = 0, 0, 0 # Initial position and direction

    for _ in range(m * n):
        res.append(mat[r][c])
        vis[r][c] = True
        
        # Calculate the next cell's coordinates
        newR, newC = r + dr[idx], c + dc[idx]

        # If the next cell is out of bounds or visited, change direction
        if not (0 <= newR < m and 0 <= newC < n and not vis[newR][newC]):
            idx = (idx + 1) % 4 # Turn clockwise
        
        # Move to the next cell
        r += dr[idx]
        c += dc[idx]
    
    return res

def run_spiral_matrix_logic(file):
    """
    Sets up and runs the spiral matrix traversal example,
    writing output to the given file.
    """
    mat = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
        [13, 14, 15, 16]
    ]
    res = spirallyTraverse(mat)

    file.write("--- Running Spiral Matrix Traversal ---\n")
    file.write("Matrix:\n")
    for row in mat:
        file.write(str(row) + "\n")
    file.write("\nSpiral Traversal Result:\n")
    file.write(" ".join(map(str, res)) + "\n")


# --- Stack Implementation Code ---

class Node:
    """A node in a singly linked list."""
    def __init__(self, value):
        self.value = value
        self.next = None

class Stack:
    """A stack implementation using a linked list."""
    def __init__(self):
        """Initializes an empty stack with a dummy head node."""
        self.head = Node("head")
        self.size = 0

    def __str__(self):
        """String representation of the stack."""
        cur = self.head.next
        out = ""
        while cur:
            out += str(cur.value) + " -> "
            cur = cur.next
        return out[:-4] if out else "Stack is empty."

    def getSize(self):
        """Returns the current size of the stack."""
        return self.size

    def isEmpty(self):
        """Checks if the stack is empty."""
        return self.size == 0

    def peek(self):
        """Returns the top item of the stack without removing it."""
        if self.isEmpty():
            return None
        return self.head.next.value

    def push(self, value):
        """Pushes a value onto the top of the stack."""
        node = Node(value)
        node.next = self.head.next
        self.head.next = node
        self.size += 1

    def pop(self):
        """Removes and returns the top value from the stack."""
        if self.isEmpty():
            raise IndexError("Popping from an empty stack")
        remove = self.head.next
        self.head.next = remove.next
        self.size -= 1
        return remove.value

def run_stack_logic(file):
    """
    Runs the stack implementation example,
    writing output to the given file.
    """
    stack = Stack()
    file.write("--- Running Stack Implementation ---\n")
    file.write(f"Initial Stack: {stack}\n")

    file.write("\nPushing numbers 1 to 10 onto the stack...\n")
    for i in range(1, 11):
        stack.push(i)
    file.write(f"Stack after pushes: {stack}\n")
    file.write(f"Current top element (peek): {stack.peek()}\n")
    file.write(f"Current stack size: {stack.getSize()}\n")

    file.write("\nPopping 5 elements from the stack...\n")
    for _ in range(5):
        popped_value = stack.pop()
        file.write(f"Popped: {popped_value}\n")

    file.write(f"\nFinal Stack: {stack}\n")
    file.write(f"Final stack size: {stack.getSize()}\n")


# --- Main Program Logic ---

def main():
    """
    Main function to handle user input and direct program flow.
    The program will write to a file and exit after one operation.
    """
    output_filename = 'output.txt'
    
    print("==============================")
    print("Choose an option:")
    print("1: Spiral Matrix Traversal")
    print("2: Stack Implementation")
    print("==============================")
    
    choice = input("Enter your choice (1 or 2): ")

    # Open the file and perform the chosen operation
    with open(output_filename, 'w') as file:
        if choice == '1':
            run_spiral_matrix_logic(file)
        elif choice == '2':
            run_stack_logic(file)
        else:
            file.write("Invalid choice entered.\n")
    
    print(f"\nOperation complete. Output has been written to {output_filename}")

if __name__ == "__main__":
    main()
