package cmd

import (
	"bufio"
	"bytes"
	"fmt"
	"os/exec"
	"strings"
)

var knownPackages = map[string]string{
	"firefox":         "Mozilla.Firefox",
	"firefox-dev":     "Mozilla.Firefox.DeveloperEdition",
	"firefox-nightly": "Mozilla.Firefox.Nightly",
	"chrome":          "Google.Chrome",
	"chromium":        "Google.Chromium",
	"edge":            "Microsoft.Edge",
	"brave":           "Brave.Brave",
	"vim":             "vim.vim",
	"neovim":          "Neovim.Neovim",
	"vscode":          "Microsoft.VisualStudioCode",
	"code":            "Microsoft.VisualStudioCode",
	"spotify":         "Spotify.Spotify",
	"discord":         "Discord.Discord",
	"obsidian":        "Obsidian.Obsidian",
	"7zip":            "7zip.7zip",
	"vlc":             "VideoLAN.VLC",
	"gimp":            "GIMP.GIMP",
	"blender":         "BlenderFoundation.Blender",
	"obs":             "OBSProject.OBSStudio",
	"steam":           "Valve.Steam",
	"git":             "Git.Git",
	"python":          "Python.Python.3.13",
	"nodejs":          "OpenJS.NodeJS",
	"docker":          "Docker.DockerDesktop",
}

func beat(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: mochi beat <package>...")
	}

	if isWindows() {
		for _, pkg := range args {
			fmt.Printf("beating %s... ", pkg)
			err := beatWinget(pkg)
			if err != nil {
				fmt.Println("failed")
				return err
			}
			fmt.Println("done!")
		}
		return nil
	}

	pacmanPkgs := []string{}
	for _, pkg := range args {
		if id, ok := knownPackages[strings.ToLower(pkg)]; ok {
			fmt.Printf("beating %s via flatpak...\n", pkg)
			err := runFlatpak(id)
			if err != nil {
				return err
			}
		} else {
			pacmanPkgs = append(pacmanPkgs, pkg)
		}
	}
	if len(pacmanPkgs) > 0 {
		return runPacman(append([]string{"-S", "--needed"}, pacmanPkgs...)...)
	}
	return nil
}

func beatWinget(pkg string) error {
	// Check known packages map first (no search needed, avoids wrong picks)
	if id, ok := knownPackages[strings.ToLower(pkg)]; ok {
		return runWinget("install", "--id", "--exact", "--disable-interactivity", "--accept-package-agreements", "--accept-source-agreements", id)
	}

	// Resolve short name to exact ID via search, then install by ID
	id, err := resolvePackage(pkg)
	if err != nil {
		// Maybe it's an ID already — try direct
		return runWinget("install", "--id", "--exact", "--disable-interactivity", "--accept-package-agreements", "--accept-source-agreements", pkg)
	}

	return runWinget("install", "--id", "--exact", "--disable-interactivity", "--accept-package-agreements", "--accept-source-agreements", id)
}

func runFlatpak(id string) error {
	// ensure flathub remote exists
	exec.Command("flatpak", "remote-add", "--if-not-exists", "flathub", "https://flathub.org/repo/flathub.flatpakrepo").Run()
	c := exec.Command("flatpak", "install", "-y", "flathub", id)
	out, err := c.CombinedOutput()
	if err != nil {
		return fmt.Errorf("flatpak install %s failed: %w\n%s", id, err, string(out))
	}
	fmt.Print(string(out))
	return nil
}

func resolvePackage(query string) (string, error) {
	c := exec.Command("winget", "search", "--accept-source-agreements", query)
	var outBuf bytes.Buffer
	c.Stdout = &outBuf

	if err := c.Run(); err != nil {
		return "", fmt.Errorf("no package found matching '%s'", query)
	}

	sc := bufio.NewScanner(strings.NewReader(outBuf.String()))
	var ids []string
	for sc.Scan() {
		line := sc.Text()
		if len(line) < 10 || strings.Contains(line, "---") || strings.Contains(line, "Name ") {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) < 3 {
			continue
		}
		source := strings.ToLower(parts[len(parts)-1])
		if source != "winget" && source != "mochi" {
			continue
		}
		ids = append(ids, parts[len(parts)-2])
	}

	if len(ids) == 0 {
		return "", fmt.Errorf("no package found matching '%s'", query)
	}

	return pickBest(ids, query), nil
}

func pickBest(ids []string, query string) string {
	queryLower := strings.ToLower(query)

	// If any ID matches the query exactly, use it
	for _, id := range ids {
		if strings.EqualFold(id, query) {
			return id
		}
	}

	// Match query against the name part after publisher prefix
	// e.g. "firefox" matches "Mozilla.Firefox" over "Mozilla.Firefox.DeveloperEdition"
	for _, id := range ids {
		parts := strings.Split(id, ".")
		for _, part := range parts {
			if strings.EqualFold(part, queryLower) {
				return id
			}
		}
	}

	// Prefer the shortest ID (base package, not editions/variants)
	best := ids[0]
	bestParts := strings.Count(best, ".")
	for _, id := range ids[1:] {
		parts := strings.Count(id, ".")
		if parts < bestParts {
			best = id
			bestParts = parts
		}
	}

	// Prefer non-MSIX among same-depth IDs
	for _, id := range ids {
		if strings.Count(id, ".") == bestParts && !strings.HasSuffix(strings.ToLower(id), ".msix") {
			return id
		}
	}

	return best
}
