def maxRectSum(mat):
    n = len(mat)
    m = len(mat[0])
    maxSum = float('-inf')

    for up in range(n):
        for left in range(m):
            for down in range(up, n):
                for right in range(left, m):
                    
                    # Calculate the sum of submatrix 
                    # (up, left, down, right)
                    subMatrixSum = 0
                    for i in range(up, down + 1):
                        for j in range(left, right + 1):
                            subMatrixSum += mat[i][j]

                    # Update maxSum if a larger sum is found
                    maxSum = max(maxSum, subMatrixSum)

    return maxSum


if __name__ == "__main__":
    
    mat = [
        [1, 2, -1, -4, -20],
        [-8, -3, 4, 2, 1],
        [3, 8, 10, 1, 3],
        [-4, -1, 1, 7, -6]
    ]

    print(maxRectSum(mat))