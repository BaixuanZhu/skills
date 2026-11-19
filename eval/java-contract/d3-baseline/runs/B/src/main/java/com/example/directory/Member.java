package com.example.directory;

/** 外部导入的成员记录，字段都可能没有值。 */
public final class Member {

    private final String id;
    private final String name;
    private final String team;
    private final Integer age;

    public Member(String id, String name, String team, Integer age) {
        this.id = id;
        this.name = name;
        this.team = team;
        this.age = age;
    }

    public String getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public String getTeam() {
        return team;
    }

    public Integer getAge() {
        return age;
    }
}
