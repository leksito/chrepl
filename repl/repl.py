from console import Cmd
import cmd


if __name__ == '__main__':
    for command in Cmd().cmd_generator():
        print(command)
