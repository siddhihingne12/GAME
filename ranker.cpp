#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <map>

// A high-performance ranking utility for Memory Master
// This can be used to process large leaderboards on the server side

struct Player {
    std::string name;
    int score;
    double time;
};

bool comparePlayers(const Player& a, const Player& b) {
    if (a.score != b.score) {
        return a.score > b.score; // Higher score first
    }
    return a.time < b.time; // Lower time first for same score
}

int main() {
    std::vector<Player> players = {
        {"Cipher_Master", 1240, 45.2},
        {"Nexus_Brain", 1120, 48.5},
        {"Quantum_Mind", 1240, 42.1},
        {"Master_Player", 950, 50.0}
    };

    std::sort(players.begin(), players.end(), comparePlayers);

    std::cout << "RANK | PLAYER | SCORE | TIME" << std::endl;
    std::cout << "---------------------------" << std::endl;
    for (size_t i = 0; i < players.size(); ++i) {
        std::cout << (i + 1) << " | " << players[i].name << " | " << players[i].score << " | " << players[i].time << "s" << std::endl;
    }

    return 0;
}
