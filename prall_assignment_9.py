from CoffeeOrder import CoffeeOrder  # Imports Coffee Class
"""
Using Assignment 8 where you constructed a class that included mutator and accessor methods to support encapsulation, 
you want to add the following modifications to the class file and also (where appropriate) changes to support the processing of exceptions (runtime errors).  
For this assignment, you will add exception processing for the class object coffee cost instance variables.

Assignment Requirements:

Using Assignment 8:

    Your app should contain try/catch logic so that an exception raised the coffee cost class mutator method will process exceptions for a letter value (value exception or the python ValueError exception) 
    and less than zero with an error message and allow the user to fix the value entered.
    (Optional) - create a solution and test in python.

 Type the answer in a text document and submit to Canvas.

"""


order = CoffeeOrder.create_default_coffee()  # Create coffee class object
Tries = 0  # Number of Tries to enter correct coffee
while Tries < 3:  # Loop with 3 Tries
    try:  # try to get correct input
        order.coffeeType = input(
            "Enter The Type of Coffee: ")  # Input coffee type
        order.size = input("Enter The Size of Coffee: ")  # Input coffee size
        order.cost = input(
            "Enter cost or enter d for default: ")  # Input price
        Tries = 99  # Set tries to 99 to indicate ok
    except ValueError as error:  # if input fails catch Error
        print(error)  # Print Error
        Tries += 1  # Increase counter by one
    except Exception as error:  # if input fails catch Error
        print(error)  # Print Error
        Tries += 1  # Increase counter by one
    finally:  # Finally block
        if Tries == 99:  # If ok
            order.print_label()  # print label
        elif Tries < 3:  # if not ok but tries left
            print('Please try again.')
        else:  # if tries exceeded
            print('Please start over')
