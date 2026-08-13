Feature: Authentication
  As a user
  I want to log in and log out
  So that I can access the system securely

  @smoke
  Scenario: Successful login
    Given I am on the login page
    When I enter valid credentials
    Then I should be logged in
    And I should see the dashboard

  @smoke @fast
  Scenario: Failed login with wrong password
    Given I am on the login page
    When I enter invalid credentials
    Then I should see an error message
    And I should not be logged in

  @slow
  Scenario: Account lockout after 3 attempts
    Given I am on the login page
    When I enter invalid credentials 3 times
    Then my account should be locked
    And I should see a lockout message

  @regression
  Scenario: Logout clears session
    Given I am logged in
    When I click logout
    Then my session should be cleared
    And I should be redirected to login
