package cmd

import "fmt"

func deploy(args []string) error {
	if !hasAbroot() {
		return fmt.Errorf("abroot not available on this system")
	}
	fmt.Println("deploying to inactive root...")
	cmdArgs := []string{"deploy"}
	cmdArgs = append(cmdArgs, args...)
	return runAbroot(cmdArgs...)
}
