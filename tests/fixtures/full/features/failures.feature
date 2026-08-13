Feature: Failing scenarios
  As a developer
  I want to test failure handling
  So that I can verify retry behavior

  @smoke
  Scenario: Intentional failure
    Given I have a failing step
    Then the scenario should fail

  @regression
  Scenario: Another intentional failure
    Given I have a failing step
    Then the scenario should fail
