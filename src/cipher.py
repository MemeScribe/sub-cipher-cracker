import sys, time, string
from multiprocessing import Process, Queue, current_process

# Pass encoded text, English library, a shift amount seed and the process queue to a caesar process
def caesar(line, library, seed, queue):
    # Have each process perform 3 shifts each unless the corect key is found before then
    for i in range(0,3):
        # Generate key by seed+i shifts
        key = {s: chr(((ord(s)-97 + seed+i) % 26)+97) for s in string.ascii_lowercase}
        shift = ""
        # tanslate the text using the key
        for char in punctuation(line):
            try:
                shift += key[char.lower()]
            except KeyError:
                shift += char
        # generate a list of words that are in the English library and test if over 60% of them are considered English
        english = [word for word in shift.split() if word in library]
        english,shiftSet = [set(english), set(shift.split())]
        if len(shiftSet) - len(english) < len(shiftSet) * 0.4:
            print("Process",current_process().name,"finished: success")
            # place the key in the queue to act as a return statement
            queue.put(key)
        # print("pass",seed+i)
    print("Process",current_process().name,"finished: failed")

# Passing the encoded text, English library and process queue to the substitution process
def substitution(line, library, queue):
    key = {}
    # frequency analysis for letters and words sorted my most common to least common
    commonWords = freqWord(line)
    commonLetters = freqChar(line)
    # assign the most common letter to "e"
    key[max(commonLetters, key=lambda key: commonLetters[key])] = "e"
    # create a list of tuples with each tuple containing a word and the word previous
    lineZip = list(zip(line.split()[1:], line.split()))
    for word in lineZip:
        # If there is a lowercase leter of length 1, assignt it to "a"
        if len(word[0]) == 1 and word[0].islower():
            key[word[0]] = "a"
        # If there is an uppercase letter of length 1 that is not at the start of a sentence, assing it to "i"
        elif len(word[0]) == 1 and word[1][-1] != ".":
            key[word[0].lower()] = "i"
        # If there is a word of length 4 where the second and third are the same and they aren't "e", assign them to "o"
        if len(word[0]) == 4 and word[0][1] == word[0][2] and word[0][1] != getKey("e", key):
            key[word[0][1]] = "o"

    for word in commonWords:
        # find the most common 3 letter word that begins with "a", assign letter 2 as "n" and letter 3 as "d"
        if word[0] == getKey("a", key) and len(word) == 3 and word[1] != word[2] and word[1] not in key.keys() and word[2] not in key.keys():
            key[word[1]] = "n"
            key[word[2]] = "d"
        # find a 3 letter word that begins with a and letters 2 and 3 are the same, assign them "l"
        elif word[0] == getKey("a", key) and len(word) == 3 and word[1] == word[2]:
            key[word[1]] = "l"
        # find the most common 3 letter word that ends with "e", assign letter 1 as "t" and letter 2 as "h"
        elif len(word) == 3 and word[2] == getKey("e", key) and "t" not in key.values():
            key[word[0].lower()] = "t"
            key[word[1]] = "h"

    if "i" not in key.values():
        # if I wan't found, grab every 2 letter word where "t" is the second letter and letter 1 hasn't been found, assign letter 1 to "i" if found
        twoLetters = [x.lower() for x in commonWords if len(x) == 2 and x[-1] == getKey("t", key) and x[0].lower() not in key.keys()]
        if len(twoLetters) > 0:
            key[twoLetters[0][0].lower()] = "i"
        #find every 2 letter word that ends whit "n" and where letter 1 is not found, assign it to "o"
        twoLetters = [x[0] for x in commonWords if len(x) == 2 and x[-1] == getKey("n", key)]
        for twoWord in twoLetters:
            if twoWord[0].lower() not in key.keys():
                key[twoWord[0].lower()] = "o"
    # print(key)
    # While this method is finding letters, check every word again
    prevLen = 0
    while prevLen != len(key):
        prevLen = len(key)
        # find every word where only one letter is missing from our key
        for word in commonWords:
            counter = [x for x in word if x not in key.keys()]
            if len(counter) == 1:
                similarList = []
                for x in word:
                    # Assign the missing letter as a variable
                    if x not in key.keys():
                        outlier = x.lower()
                # mark the outlier's position with a non-alnum character so decoding doesn't confuse the program
                # such as when the outlier letter is the same as a decoded letter
                word = decoded(word.replace(outlier,"%"), key)
                # find every English word with the same length as our word and undergo a letter match check and a structure check
                candidates = [x for x in library if len(x) == len(word)]
                for candidate in candidates:
                    if similar(word, candidate):
                        # If word is considered similar, append it to a list of similar words
                        similarList.append(candidate)
                # If we only found a single match for our word, we can safely map the outlier to the English words's counterpart
                if len(similarList) == 1:
                    winner = similarList[0]
                    for i in winner:
                        if i.lower() not in key.values():
                            key[outlier.replace("%",outlier)] = i.lower()
                            # print(outlier,":", i)
                            # print(word.replace("%", outlier), winner)

    # While this method is matching letters, run the loop again
    prevLen = 0
    while prevLen != len(key) and len(key) < 26:
        prevLen = len(key)
        # grab every encoded letter in order of frequency and unmatched letters
        tempList = [x for x in "abcdefghijklmnopqrstuvwxyz" if x not in key.keys()]
        leftoverKey = [x for x in commonLetters if x in tempList]
        leftoverValue = [x for x in "abcdefghijklmnopqrstuvwxyz" if x not in key.values()]
        # if we're only missing one letter, match it with the only possible letter
        if len(leftoverValue) == 1:
            key[tempList[0]] = leftoverValue[0]
        else:
            # for each encoded letter, grab every word which contains it
            for encoded in leftoverKey:
                leftoverWords = [y for y in commonWords if encoded in y]
                dictCorrect = {}
                # for each unmatched letter, go through each word and replace the encoded letter with the unmatched letter.
                for unmatched in leftoverValue:
                    attempt = [decoded(z.replace(encoded,"%"), key) for z in leftoverWords]
                    # print(unmatched, [s.replace("%", unmatched) for s in attempt])
                    # Have each English word that is made with this process added to it's "correct score"
                    correct = len([z.replace("%",unmatched) for z in attempt if z.replace("%",unmatched) in library or "un"+z.replace("%",unmatched) in library])
                    dictCorrect[unmatched] = correct
                # print(dictCorrect)
                # if only 1 letter has the most correct words, assign it to the encoded letter
                if len(dictCorrect) > 0 and list(dictCorrect.values()).count(max(dictCorrect.values())) == 1:
                    key[encoded] = max(dictCorrect, key=lambda key: dictCorrect[key])
                    leftoverValue.remove(key[encoded])
                    leftoverKey.remove(encoded)
                    # print("Winner:", key[encoded])
                # otherwise skip assignment to come back when more keys might be found
                else:
                    pass
    # If more than one letter is missing from the text, then we can't find full key without pure guesswork, assign each missing letter with None
    none = [x for x in "abcdefghijklmnopqrstuvwxyz" if x not in commonLetters]
    for letter in none:
        key[letter] = None
    print("substitution finished")
    # place the key in the process queue to act as a return statement
    queue.put(key)

# returns a dictionary with each letter in the encoded text sorted most common to least common
def freqChar(line):
    counter = {}
    for char in line:
        if char.isalpha():
            try:
                counter[char] = counter[char] + 1
            except KeyError:
                counter[char] = 0
    return {k: v for k, v in sorted(counter.items(), key=lambda item: item[1], reverse=True)}

# returns a dictionary with each word in the encoded text sorted most common to least common
def freqWord(line):
    counter = {}
    line = punctuation(line)
    for word in line.split():
        try:
            counter[word] = counter[word] + 1
        except KeyError:
            counter[word] = 0
    return {k: v for k, v in sorted(counter.items(), key=lambda item: item[1], reverse=True)}

# return the key from the value in a key
def getKey(val, dic):
    for key, value in dic.items(): 
         if val == value: 
             return key

# return the string with all known letters decoded and unknown letters unchanged
def decoded(word, key):
    decode = ""
    for char in word:
        if char.isupper():
            try:
                decode += key[char.lower()].upper()
            except KeyError:
                decode += char
        else:
            try:
                decode += key[char.lower()]
            except KeyError:
                decode += char
    return decode

# check if there is only a single letter difference between an almost decoded word and an English word
def similar(testWord, baseWord):
    testWordLetters = "".join(set(testWord))
    baseWordLetters = "".join(set(baseWord))
    outlier = []
    try:
        for baseChar in baseWordLetters:
            if baseChar not in testWordLetters:
                outlier.append(baseChar)
    except IndexError:
        pass
    if len(outlier) > 1:
        return False
    # check word structure matches
    elif len(outlier) == 1:
        structureTest = testWord
        structureTest = structureTest.replace("%", outlier[0])
        # print(testWord, baseWord, structureTest)
        return structureTest == baseWord
    return False

# return a string with punctuation removed
def punctuation(word):
    return word.translate(str.maketrans('', '', string.punctuation))

# grab the web2 document in the repo home and convet it into a list to use for various word comparisons
def libGen():
    l = []
    with open("../web2", "r") as f:
        for line in f.readlines():
            l.append(line.strip())
        return l

# Start by initialising a timer for testing purposes
# Generate our English word library to let our program know what what words are correctly deciphered
def main():
    start = time.time()
    library = libGen()
    # Take input file name from command-line argument
    inputName = sys.argv[1]
    with open(inputName, "r") as line:
        line = line.read()
        # create a multi-process Queue to allow spwned processes to return the deciphered key
        queue = Queue()
        # Spawn 9 caesar processes and have them search 3 shifts in the alphabet each
        romanGathering = []
        for i in range(0,9):
            c = Process(target=caesar, name="ceasar-"+str(i+1), args=(line, library, i*3, queue,))
            c.start()
            romanGathering.append(c)
        # Spawn a single substitution process as spawning more doesn't speed up the program
        s = Process(target=substitution, name="substitution" , args=(line, library, queue,))
        s.start()
        # wait for the a key to be put in Queue before continuing 
        while queue.qsize() == 0:
            pass
        result = queue.get()
        # grab the key from the queue first before terminating all processes, doing so out of order causes the script to hang
        for c in romanGathering:
            c.terminate()
        s.terminate()
        # check if Substitution determined if there are too many missing letters to grab the full key and display a warning if that is the case
        if list(result.values()).count(None) > 1:
            print("Warning, This message is missing 2 or more letters, This means that it is impossible to get the full key from the given text.")
            print("The key printed in \'"+inputName[:-4]+"-key.txt\' should contain everything needed to decode the cipher and missing letters are marked as None.")
        deciphered = ""
        # Use the key to generate the deciphered text
        for char in line:
            try:
                deciphered += result[char.lower()]
            except KeyError:
                deciphered += char
        # write the key to [inputName]-key.txt
        with open(inputName[:-4]+"-key.txt", "w") as key:
            for k,v in result.items():
                if v == None:
                    key.write("None = "+k+"\n")
                else:
                    key.write(v+" = "+k+"\n")
        # write the deciphered text to [inputName]-decrypted.txt
        with open(inputName[:-4]+"-decrypted.txt", "w") as solution:
            solution.write(deciphered)
    # print to time it took for the program to run for testing purposes
    print("Program runtime:",time.time() - start)

if __name__ == '__main__':
    main()
