'''
Using the logic designed for Assignment Six, create a sequential text file that contains the test data defined in assignment six.  
Read this file into the two arrays used to create a linear search of the coffee type to find the caffeine factor (as you did in assignment 6).  
This would be one file but loading two arrays. 
Create an ASCII text file with test data to load into coffee name  and caffeine arrays
Optional: You can need to create a PYTHON program to test that the logic would implement and test this solution.
'''


import csv


print('Starting program...')


try:
    with open("coffeeArray.csv", newline='') as coffeeArray: # Open File
        data = list(csv.reader(coffeeArray)) # Get Data
except IOError: # Exception catch
    print("File does not exist") # Print Error 
except Exception as error:  # if catch fails catch general Error
    print(error)  # Print Error

coffeeArray = data[0]
caffeineArray = data[1]


def get_caffine(coffeeType='regular'):
    Tries = 0  # Number of Tries to enter correct coffee
    while Tries < 3:  # Loop with 3 Tries
        try:  # try to get correct input
            # Input for name of coffee
            coffeeType = input("Enter The Name of the coffee: ")
            if coffeeType.lower() in coffeeArray:  # if the coffee type is in the array
                coffeeIndex = coffeeArray.index(
                    coffeeType)  # Get the array index
                # Get the caffeine by index
                caffeineLevel = caffeineArray[coffeeIndex]
                return coffeeType, int(caffeineLevel)  # return two varibles
            print(f'{coffeeType} not in {coffeeArray}')  # print if failed
            Tries += 1  # increase the counter by 1
        except Exception as error:  # if input fails catch Error
            print(error)  # Print Error
            Tries += 1  # Increase counter by one


try:
    coffeeType, caffeineLevel = get_caffine()  # get both varibles
    # print the caffeine levels
    print(f'Caffeine Level for {coffeeType} is {caffeineLevel}')
except TypeError:
    print('Failed Restart Program')  # 3 tries failed restart program
except Exception as error:  # if input fails catch Error
    print(error)  # Print Error
