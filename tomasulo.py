def main():
    print("ECE 2162 - Project 1","Jefferson Boothe","James Bickerstaff","--------------------",sep="\n")

    print("Loading instructions...")
    f = open('instructions.txt', 'r')
    inst_lines = f.readlines()
    inst_lines = [s.lower().strip() for s in inst_lines]
    for line in inst_lines:
        print(line)
    print("--------------------")

if __name__ == '__main__':
    main()