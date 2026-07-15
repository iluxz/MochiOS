package cmd

import "fmt"

func deploy(args []string) error {
	if isWindows() {
		return fmt.Errorf("mochi deploy is a mochios-only command (try winget upgrade)")
	}
	if !hasAbroot() {
		return fmt.Errorf("abroot not available on this system")
	}
	fmt.Println("deploying to inactive root...")
	cmdArgs := []string{"deploy"}
	cmdArgs = append(cmdArgs, args...)
	return runAbroot(cmdArgs...)
}
