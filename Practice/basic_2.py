# One way to import all functions from basic_1.py
#from basic_1 import greet_user, calculate_sum, find_maximum, greet_user, reverse_string, get_user_info

#print(greet_user("Raihan"))
#print("Sum:", calculate_sum(5, 10))
#print("Maximum:", find_maximum([3, 1, 4, 1, 5, 9]))
#print("Reversed String:", reverse_string("Hello"))
#print("User Info:", get_user_info(1, 30, "active"))


# Another way to import the entire module (Import with Alias (Nickname))
import Practice.basic_1 as b1

print(b1.greet_user("Raihan"))
print("Sum:", b1.calculate_sum(5, 10))
print("Maximum:", b1.find_maximum([3, 1, 4, 1, 5, 9]))
print("Reversed String:", b1.reverse_string("Hello"))
print("User Info:", b1.get_user_info(1, 30, "active"))