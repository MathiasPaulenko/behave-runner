Feature: Pokémon API

  @smoke
  Scenario: Get pokemon by name
    Given I request pokemon "pikachu"
    Then the response status should be 200
    And the pokemon name should be "pikachu"
    And the pokemon should have stats

  Scenario: Get pokemon by invalid name
    Given I request pokemon "nonexistentpokemon123"
    Then the response status should be 404
