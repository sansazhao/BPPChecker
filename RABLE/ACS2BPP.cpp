#include <bits/stdc++.h>
using namespace std;

int main(int argc, char* argv[]) {
    string acs_file = "acs/ring_acs";
    string bpp_file = "acs/ring_bpp";
    if (argc > 1) {
        acs_file = argv[1];
        bpp_file = argv[2];
    }
    freopen(acs_file.c_str(),"r",stdin);
    freopen(bpp_file.c_str(),"w",stdout);
    string str;
    int pid, pos;
    while (getline(cin, str)) {
        if (str.substr(0, 3) == "Pid") {
            pid = atoi(str.substr(4, str.length() - 5).c_str());
            if (pid == 0) cout << "initial\ns1\n\nrules\n";
            else cout << endl;
        }
        else if (str == "") continue;
        else {
            // spawn
            if ((pos = str.find("vPid")) != string::npos) { 
                for (int i = 0; i < pos-1; i++) cout << str[i];
                cout << ", s";
                pos = str.find('.');
                cout << str.substr(pos+1) << endl;
            }
            // send message
            else if ((pos = str.find("!")) != string::npos) { 
                pos = str.find("Pid");
                for (int i = 0; i < pos-1; i++) cout << str[i];
                cout << ", m";
                int sendTo = 0, msg = 0;
                for (int i = pos + 3; str[i] != ' '; i++) sendTo = sendTo * 10 + str[i] - '0';
                pos = str.find_last_of(' ');
                msg = atoi(str.substr(pos + 1).c_str());
                cout << sendTo << '_' << msg << "in\n";
            }
            // receive message
            else if ((pos = str.find("?")) != string::npos) { 
                for (int i = 0; i < pos-1; i++) cout << str[i];
                cout << ", m" << pid << '_';
                pos = str.find_last_of(' ');
                int msg = atoi(str.substr(pos + 1).c_str());
                cout << msg << "out\n";
            }
            // general situation
            else {
                cout << str << endl;
            }
        }
    }
    fclose(stdin);fclose(stdout);
    return 0;
}