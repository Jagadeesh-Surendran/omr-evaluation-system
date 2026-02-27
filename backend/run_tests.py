import subprocess

result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-v'], capture_output=True, text=True)
with open('test.log', 'w', encoding='utf-8') as f:
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\nSTDERR:\n")
    f.write(result.stderr)
