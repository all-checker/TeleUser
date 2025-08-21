#!/usr/bin/env python3
"""
Regenerate username combination files
Usage: python3 regenerate_files.py
"""
import itertools
import string
import random

def generate_4letter_combinations():
    """Generate all possible 4-character combinations (alphabetic only)"""
    characters = string.ascii_lowercase + string.ascii_uppercase
    
    print(f"Generating all 4-character combinations...")
    print(f"Total possible combinations: {len(characters)**4:,}")
    
    count = 0
    with open("usernames.txt", 'w') as f:
        for combo in itertools.product(characters, repeat=4):
            username = ''.join(combo)
            f.write(username + '\n')
            count += 1
            
            if count % 100000 == 0:
                print(f"Generated {count:,} combinations...")
    
    print(f"✅ Completed! Generated {count:,} combinations in usernames.txt")

def generate_combinations_subset(length, output_file, max_combinations=1000000):
    """Generate random combinations of given length (alphabetic only)"""
    characters = string.ascii_lowercase + string.ascii_uppercase
    
    total_possible = len(characters) ** length
    print(f"\nGenerating {length}-character combinations...")
    print(f"Total possible combinations: {total_possible:,}")
    print(f"Generating {max_combinations:,} random combinations...")
    
    combinations = set()
    while len(combinations) < max_combinations:
        combo = ''.join(random.choices(characters, k=length))
        combinations.add(combo)
        
        if len(combinations) % 100000 == 0:
            print(f"Generated {len(combinations):,} unique combinations...")
    
    # Write to file
    with open(output_file, 'w') as f:
        for combo in sorted(combinations):
            f.write(combo + '\n')
    
    print(f"✅ Completed! Generated {len(combinations):,} combinations in {output_file}")

def main():
    """Generate all combination files"""
    print("🚀 Regenerating username combination files...")
    print("📝 Using only alphabetic characters (a-z, A-Z)")
    print("=" * 60)
    
    # Generate 4-letter combinations (complete set)
    generate_4letter_combinations()
    
    # Generate 5, 6, 7-letter combinations (random subsets)
    generate_combinations_subset(5, "5letter.txt", 1000000)
    generate_combinations_subset(6, "6letter.txt", 1000000)
    generate_combinations_subset(7, "7letter.txt", 1000000)
    
    print("\n" + "=" * 60)
    print("✅ All username files regenerated successfully!")
    print("📁 Files created:")
    print("   - usernames.txt (7,311,616 combinations)")
    print("   - 5letter.txt (1,000,000 combinations)")
    print("   - 6letter.txt (1,000,000 combinations)")
    print("   - 7letter.txt (1,000,000 combinations)")
    print("\n🚀 Ready to run: python3 telebot_fast.py")

if __name__ == "__main__":
    main()