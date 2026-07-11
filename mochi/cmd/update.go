package cmd

import "fmt"

func updateCmd(args []string) error {
	if hasAbroot() {
		fmt.Println("updating via abroot...")
		return runAbroot("deploy")
	}
	fmt.Println("updating via pacman...")
	return runPacman("-Syu")
}
