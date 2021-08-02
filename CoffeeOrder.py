from datetime import datetime as dt


class CoffeeOrder:
    COFFEES = ["regular", "decaf", "latte",
               "steamer"]  # Class Attribute Constant
    SIZES = ["small", "medium", "large",
             "extra large"]  # Class Attribute Constant
    PRICES = [1.00, 1.75, 2.25, 2.50]  # Class Attribute Constant
    LABEL_WIDTH = 23  # Class Attribute Constant

    def __init__(self,
                 coffeeType="regular",
                 size="small",
                 cost='default'):  # initialize method with default values
        print("Starting coffee shop")  # Log
        self.coffeeType = str(coffeeType)  # Instance Attribute type of coffee
        self.size = str(size)  # Instance Attribute size of coffee
        self.cost = cost

    @property
    def coffeeType(self) -> str:  # Property public
        return self.__coffeeType

    @coffeeType.setter
    def coffeeType(self, coffeeType):  # Setter (Mutator)
        if not (coffeeType.lower()
                in self.COFFEES):  # if the coffee type is in the array
            raise ValueError("Coffee Type is NOT valid")  # Raise error
        self.__coffeeType = str(coffeeType)  # Set

    @property
    def size(self) -> str:  # Property public
        return self.__size

    @size.setter
    def size(self, size):  # Setter (Mutator)
        if not ((size.lower())
                in self.SIZES):  # if the size is not in the size array
            raise ValueError("Size is NOT valid")  # Raise error
        self.__size = str(size)  # Set

    @property
    def productID(self) -> str:  # Property read only (Accessor)
        return self.__coffeeType[:3].title() + str(
            (self.SIZES.index(self.size.lower())
             ))  # Create ID by first three letters of coffee + size

    @property
    def cost(self) -> float:  # Property
        return self.__cost

    @cost.setter
    def cost(self, cost='default'):  # Property
        try:  # try for number
            cost = float(cost)  # turn into float
            if cost >= 0:  # if greater than zero
                self.__cost = cost  # return cost
            else:
                raise ValueError("Cost must be greater than 0"
                                 )  # if less than zero raise error
        except ValueError:  # if not number must be string
            if cost.lower() in ('default',
                                'd'):  # If asking for default get default cost
                self.__cost = float(self.PRICES[self.SIZES.index(
                    self.size.lower())])  #set default cost
            else:
                raise KeyError(
                    'String not Recognize')  # incorrect string raise error

    @property
    def cost_str(self) -> str:  # Property read only (Accessor)
        return f"${self.cost:.2f}"  # cost in Dollars

    def print_label(self):  # Public method
        """[Prints a label with datetime and all of the class attributes]"""
        width = self.LABEL_WIDTH  # full width of the box
        now = dt.now()  # current datetime
        date_str = now.strftime("%b %m, %Y")  # convert date to string
        time_str = now.strftime("%I:%M:%S")  # convert time to string
        box = f'╔{"═" * width}╗\n'  # Top of box
        box += "".join([
            f"║{date_str}{' ' * (width - (len(date_str)+len(time_str)))}{time_str}║\n"
        ])  # First line in box
        box += "".join([
            f"║{self.coffeeType.title()}{' ' * (width - (len(self.coffeeType)+len(self.size)))}{self.size.title()}║\n"
        ])  # Second line in box
        box += "".join([
            f"║{self.cost_str}{' ' * (width - (len(self.cost_str)+len(self.productID)))}{self.productID}║\n"
        ])  # Third line in box
        box += f'╚{"═" * (width)}╝'  # Bottom of box
        print(box)

    @classmethod
    def create_default_coffee(cls):  # Class Method
        return CoffeeOrder(
            "Regular", "small",
            "default")  # Can return a default coffee class if needed
