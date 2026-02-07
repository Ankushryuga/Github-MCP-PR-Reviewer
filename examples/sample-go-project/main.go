package main

import (
	"fmt"
	"net/http"
)

// User represents a user in the system
type User struct {
	ID    int    `json:"id"`
	Name  string `json:"name"`
	Email string `json:"email"`
}

// GreetUser returns a greeting message for a user
func GreetUser(user User) string {
	return fmt.Sprintf("Hello, %s!", user.Name)
}

// HandleHealthCheck is an HTTP handler for health checks
func HandleHealthCheck(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, "OK")
}

func main() {
	user := User{
		ID:    1,
		Name:  "John Doe",
		Email: "john@example.com",
	}

	fmt.Println(GreetUser(user))

	http.HandleFunc("/health", HandleHealthCheck)
	fmt.Println("Server starting on :8080")
	http.ListenAndServe(":8080", nil)
}
