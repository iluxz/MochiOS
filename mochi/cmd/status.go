package cmd

import "fmt"

func statusCmd(args []string) error {
	if hasAbroot() {
		fmt.Println("abroot status:")
		return runAbroot("status")
	}
	fmt.Println("system: standard (no abroot)")
	return run("uname", "-r")
}
