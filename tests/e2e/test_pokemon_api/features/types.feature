Feature: Pokémon Types API

  Scenario: Get type by name
    Given I request type "electric"
    Then the response status should be 200
    And the type name should be "electric"
    And the type should have damage relations
