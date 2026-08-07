Feature: Failing tests

  Scenario: Always fails
    Given a step
    When I do something that fails
    Then I should see a failure
