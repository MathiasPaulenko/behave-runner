Feature: Saucedemo Login

  @smoke
  Scenario: Standard user login
    Given I am on the saucedemo login page
    When I login with username "standard_user" and password "secret_sauce"
    Then I should see the products page

  Scenario: Locked user cannot login
    Given I am on the saucedemo login page
    When I login with username "locked_out_user" and password "secret_sauce"
    Then I should see an error message

  Scenario: Problem user login
    Given I am on the saucedemo login page
    When I login with username "problem_user" and password "secret_sauce"
    Then I should see the products page
