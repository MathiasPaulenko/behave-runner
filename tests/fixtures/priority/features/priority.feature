Feature: Priority tests

  @priority.1
  Scenario: High priority test
    Given a step
    Then I verify priority

  @smoke
  Scenario: Smoke test
    Given a step
    Then I verify smoke

  @priority.3
  Scenario: Low priority test
    Given a step
    Then I verify priority
