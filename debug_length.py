"""Debug Length parsing."""
import sys
sys.path.insert(0, "src")

from ornata.api.exports.definitions import Length

# Test various values
test_values = ["100%", "100", "100px", "10cell", "1"]

for val in test_values:
    try:
        length = Length.from_token(val)
        if length:
            print(f"{val!r} -> value={length.value}, unit={length.unit}")
        else:
            print(f"{val!r} -> None")
    except Exception as e:
        print(f"{val!r} -> ERROR: {e}")
