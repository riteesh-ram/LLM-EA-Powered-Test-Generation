def spirallyTraverse(mat):
    """
    Traverses a matrix in a spiral (clockwise) fashion.
    """
    m = len(mat)
    n = len(mat[0])
    res = []
    vis = [[False] * n for _ in range(m)]

    # Changes in row and column indices for each direction (Right, Down, Left, Up)
    dr = [0, 1, 0, -1]
    dc = [1, 0, -1, 0]

    r, c, idx = 0, 0, 0  # Initial position and direction

    for _ in range(m * n):
        res.append(mat[r][c])
        vis[r][c] = True
        
        # Calculate the next cell's coordinates
        newR, newC = r + dr[idx], c + dc[idx]

        # If the next cell is out of bounds or visited, change direction
        if not (0 <= newR < m and 0 <= newC < n and not vis[newR][newC]):
            idx = (idx + 1) % 4  # Turn clockwise
        
        # Move to the next cell
        r += dr[idx]
        c += dc[idx]
    
    return res


def merge_sort(arr):
    """Sorts array using merge sort algorithm."""
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)


def merge(left, right):
    """Merges two sorted arrays."""
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def binary_search(arr, target):
    """Searches for target in sorted array using binary search."""
    low, high = 0, len(arr) - 1
    
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    
    return -1


def run_spiral_matrix(file):
    """Runs spiral matrix traversal and writes output to file."""
    mat = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
        [13, 14, 15, 16]
    ]
    
    result = spirallyTraverse(mat)
    
    file.write("--- Spiral Matrix Traversal ---\n")
    file.write("Original Matrix:\n")
    for row in mat:
        file.write(str(row) + "\n")
    file.write("\nSpiral Traversal Result:\n")
    file.write(" ".join(map(str, result)) + "\n")
    file.write(f"Total elements traversed: {len(result)}\n\n")


def run_sorting(file):
    """Runs merge sort and writes output to file."""
    arr = [34, 7, 23, 32, 5, 62, 11, 90, 3, 45]
    sorted_arr = merge_sort(arr)
    
    file.write("--- Array Sorting (Merge Sort) ---\n")
    file.write(f"Original array: {arr}\n")
    file.write(f"Sorted array:   {sorted_arr}\n")
    file.write(f"Array length: {len(arr)}\n\n")


def run_binary_search(file):
    """Runs binary search and writes output to file."""
    arr = [34, 7, 23, 32, 5, 62, 11, 90, 3, 45]
    sorted_arr = merge_sort(arr)
    numbers_to_find = [23, 45, 99, 5, 100]
    
    file.write("--- Binary Search ---\n")
    file.write(f"Sorted array: {sorted_arr}\n")
    file.write("Search Results:\n")
    
    for num in numbers_to_find:
        index = binary_search(sorted_arr, num)
        if index != -1:
            file.write(f"Number {num} found at index {index}\n")
        else:
            file.write(f"Number {num} not found in array\n")
    file.write("\n")


def main():
    """Main function with menu system."""
    print("=" * 50)
    print("ALGORITHM DEMONSTRATION MENU")
    print("=" * 50)
    print("1. Spiral Matrix Traversal")
    print("2. Array Sorting (Merge Sort)")
    print("3. Binary Search")
    print("=" * 50)
    
    choice = int(input("Enter your choice (1-3): "))
    
    with open('audit_log.txt', 'w') as audit_file:
        audit_file.write("ALGORITHM EXECUTION AUDIT LOG\n")
        audit_file.write("=" * 40 + "\n\n")
        
        if choice == 1:
            print("Running Spiral Matrix Traversal...")
            run_spiral_matrix(audit_file)
            print("Spiral matrix output written to audit_log.txt")
            
        elif choice == 2:
            print("Running Array Sorting...")
            run_sorting(audit_file)
            print("✓ Sorting results written to audit_log.txt")
            
        elif choice == 3:
            print("Running Binary Search...")
            run_binary_search(audit_file)
            print("Search results written to audit_log.txt")
            
        else:
            print("Invalid choice! Please select 1, 2, or 3.")
            audit_file.write("ERROR: Invalid choice selected\n")
            return
        
        audit_file.write("Execution completed successfully.\n")


if __name__ == '__main__':
    main()
