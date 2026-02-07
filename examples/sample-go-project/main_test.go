package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestGreetUser(t *testing.T) {
	tests := []struct {
		name     string
		user     User
		expected string
	}{
		{
			name: "Basic greeting",
			user: User{
				ID:    1,
				Name:  "Alice",
				Email: "alice@example.com",
			},
			expected: "Hello, Alice!",
		},
		{
			name: "Greeting with special characters",
			user: User{
				ID:    2,
				Name:  "Bob O'Brien",
				Email: "bob@example.com",
			},
			expected: "Hello, Bob O'Brien!",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := GreetUser(tt.user)
			if result != tt.expected {
				t.Errorf("GreetUser() = %v, want %v", result, tt.expected)
			}
		})
	}
}

func TestHandleHealthCheck(t *testing.T) {
	req, err := http.NewRequest("GET", "/health", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(HandleHealthCheck)
	handler.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v",
			status, http.StatusOK)
	}

	expected := "OK"
	if rr.Body.String() != expected {
		t.Errorf("handler returned unexpected body: got %v want %v",
			rr.Body.String(), expected)
	}
}
