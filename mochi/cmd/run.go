package cmd

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"

	"mochi/lang"
)

func findFile(path string) (string, error) {
	if filepath.IsAbs(path) {
		if _, err := os.Stat(path); err == nil {
			return path, nil
		}
		return "", fmt.Errorf("file not found: %s", path)
	}

	cwd, _ := os.Getwd()
	candidate := filepath.Join(cwd, path)
	if _, err := os.Stat(candidate); err == nil {
		return candidate, nil
	}

	exeDir := filepath.Dir(os.Args[0])
	for _, dir := range []string{exeDir, exeDir + "\\.."} {
		candidate = filepath.Join(dir, path)
		if resolved, err := filepath.Abs(candidate); err == nil {
			if _, err := os.Stat(resolved); err == nil {
				return resolved, nil
			}
		}
	}

	return "", fmt.Errorf("couldn't find '%s' anywhere near you (checked cwd and mochi dir)", path)
}

func runFile(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: mochi run <file> [args...]")
	}

	path, err := findFile(args[0])
	if err != nil {
		return err
	}
	rest := args[1:]
	ext := strings.ToLower(filepath.Ext(path))

	switch ext {
	case ".mochi":
		return runMochiFile(path)
	case ".py":
		return runInterpreter("python3", path, rest)
	case ".lua":
		return runInterpreter("lua", path, rest)
	case ".js", ".mjs", ".cjs":
		return runInterpreter("node", path, rest)
	case ".rb":
		return runInterpreter("ruby", path, rest)
	case ".sh":
		return runInterpreter("bash", path, rest)
	case ".ps1":
		return runInterpreter("pwsh", path, rest)
	case ".json":
		return validateJSON(path)
	case ".toml":
		return showTOML(path)
	case ".lock":
		return catFile(path)
	case ".rs":
		return compileAndRun("rustc", path, "", rest)
	case ".c":
		return compileAndRun("gcc", path, "", rest)
	case ".cpp", ".cc", ".cxx", ".c++":
		return compileAndRun("g++", path, "", rest)
	case ".cs":
		return runCS(path, rest)
	case ".java":
		return runInterpreter("java", path, rest)
	case ".bf":
		return runBrainfuckFile(path)
	case ".luau":
		return runInterpreter("lune", path, rest)
	case ".archbtw":
		return runArchBtwFile(path)
	case ".h":
		return fmt.Errorf("bro thats a header file not a program")
	case ".exe":
		return run(path, rest...)
	case ".bat", ".cmd":
		return run("cmd", append([]string{"/c", path}, rest...)...)
	case ".run":
		return run("sh", append([]string{path}, rest...)...)
	default:
		return fmt.Errorf("unsupported file extension: %s (try .mochi)", ext)
	}
}

func runMochiFile(path string) error {
	src, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("reading file: %v", err)
	}

	prog, err := lang.Parse(string(src))
	if err != nil {
		return fmt.Errorf("parse error: %v", err)
	}

	env := lang.NewEvalEnv()
	_, err = lang.Eval(prog, env)
	if err != nil {
		return fmt.Errorf("runtime error: %v", err)
	}

	return nil
}

func runInterpreter(name, path string, args []string) error {
	cmdArgs := append([]string{path}, args...)
	return run(name, cmdArgs...)
}

func compileAndRun(compiler, path, flags string, args []string) error {
	tmp := filepath.Join(os.TempDir(), "mochi-run-"+filepath.Base(path)+".out")
	defer os.Remove(tmp)

	cmdArgs := []string{path, "-o", tmp}
	if flags != "" {
		cmdArgs = append(strings.Fields(flags), cmdArgs...)
	}

	if err := run(compiler, cmdArgs...); err != nil {
		return fmt.Errorf("compilation failed: %v", err)
	}

	runArgs := append([]string{tmp}, args...)
	return run(tmp, runArgs...)
}

func runCS(path string, args []string) error {
	_, err := exec.LookPath("dotnet-script")
	if err == nil {
		return runInterpreter("dotnet-script", path, args)
	}

	out := filepath.Join(os.TempDir(), "mochi-run-"+filepath.Base(path)+".exe")
	defer os.Remove(out)

	if runtime.GOOS == "windows" {
		compiler := "C:\\Windows\\Microsoft.NET\\Framework\\v4.0.30319\\csc.exe"
		if err := run(compiler, "-out:"+out, "-nologo", path); err != nil {
			return fmt.Errorf("C# compilation failed: %v", err)
		}
		return run(out, args...)
	}

	if err := run("mcs", "-out:"+out, path); err != nil {
		return fmt.Errorf("C# compilation failed: %v", err)
	}
	return run("mono", append([]string{out}, args...)...)
}

func validateJSON(path string) error {
	src, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("reading file: %v", err)
	}

	cmd := exec.Command("python3", "-m", "json.tool")
	cmd.Stdin = strings.NewReader(string(src))
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

func showTOML(path string) error {
	cmd := exec.Command("python3", "-c", `
import tomllib, sys, json
with open(sys.argv[1]) as f:
    print(json.dumps(tomllib.load(f), indent=2))
`, path)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

func catFile(path string) error {
	src, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("reading file: %v", err)
	}
	fmt.Print(string(src))
	return nil
}

func runBrainfuckFile(path string) error {
	src, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("reading file: %v", err)
	}

	clean := strings.Map(func(r rune) rune {
		if strings.ContainsRune("><+-.,[]", r) {
			return r
		}
		return -1
	}, string(src))

	return runBrainfuck(clean)
}

func runBrainfuck(prog string) error {
	tape := make([]byte, 30000)
	ptr := 30000 / 2

	ip := 0
	for ip < len(prog) {
		switch prog[ip] {
		case '>':
			ptr++
		case '<':
			ptr--
		case '+':
			tape[ptr]++
		case '-':
			tape[ptr]--
		case '.':
			fmt.Printf("%c", tape[ptr])
		case ',':
			b := []byte{0}
			os.Stdin.Read(b)
			tape[ptr] = b[0]
		case '[':
			if tape[ptr] == 0 {
				depth := 1
				for depth > 0 {
					ip++
					if ip >= len(prog) {
						return fmt.Errorf("unmatched [")
					}
					if prog[ip] == '[' {
						depth++
					}
					if prog[ip] == ']' {
						depth--
					}
				}
			}
		case ']':
			if tape[ptr] != 0 {
				depth := 1
				for depth > 0 {
					ip--
					if ip < 0 {
						return fmt.Errorf("unmatched ]")
					}
					if prog[ip] == ']' {
						depth++
					}
					if prog[ip] == '[' {
						depth--
					}
				}
			}
		}
		ip++
	}

	return nil
}

func runArchBtwFile(path string) error {
	src, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("reading file: %v", err)
	}

	bf := compileArchBtw(string(src))
	return runBrainfuck(bf)
}

func compileArchBtw(src string) string {
	archMap := map[string]string{
		"i":      ">",
		"use":    "<",
		"arch":   "+",
		"linux":  "-",
		"btw":    ".",
		"by":     ",",
		"the":    "[",
		"way":    "]",
		"gentoo": "[-]",
	}

	var bf strings.Builder
	sc := bufio.NewScanner(strings.NewReader(src))
	sc.Split(bufio.ScanWords)

	for sc.Scan() {
		word := strings.ToLower(sc.Text())
		if bfCmd, ok := archMap[word]; ok {
			bf.WriteString(bfCmd)
		}
	}

	return bf.String()
}
