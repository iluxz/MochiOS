package cmd

import "fmt"

func updateCmd(args []string) error {
	if isWindows() {
		fmt.Print("updating all packages... ")
		err := runWinget("upgrade", "--all", "--disable-interactivity", "--accept-package-agreements", "--accept-source-agreements")
		if err != nil {
			fmt.Println("failed")
			return err
		}
		fmt.Println("done!")
		return nil
	}
	if hasAbroot() {
		fmt.Println("updating via abroot...")
		return runAbroot("deploy")
	}
	fmt.Println("updating via pacman...")
	return runPacman("-Syu")
}
