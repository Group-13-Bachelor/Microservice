from package_1 import app


def test_function():
    return "Hello, World!"


if __name__ == "__main__":
    # print(test_function())
    app.run(debug=True, port=5001)

